<template>
  <CHeader position="sticky" class="mb-4">
    <CContainer fluid>
      <CNavbarBrand href="#">
        <CImage :src="logo" height="50"/>
      </CNavbarBrand>
      <CHeaderNav class="d-none d-md-flex me-auto">
        <CNavItem v-show="loggedin">
          <CNavLink href="#/profile">Profile</CNavLink>
        </CNavItem>
        <CNavItem v-show="admin">
          <CNavLink href="#/dashboard">Dashboard</CNavLink>
        </CNavItem>
      </CHeaderNav>
      <CHeaderNav>
        <CNavItem>
          <div v-show="loggedin">
            <CButton v-show="adminoff" color="secondary" shape="rounded-pill" @click="perms">
              <CRow class="align-items-center">
                <div align="center">
                  <strong>Turn Admin On</strong>
                </div>
              </CRow>
            </CButton>
            <CButton v-show="adminon" color="secondary" shape="rounded-pill" @click="perms">
              <CRow class="align-items-center">
                <div align="center">
                  <strong>Turn Admin Off</strong>
                </div>
              </CRow>
            </CButton>
          </div>
        </CNavItem>
        <CNavItem>
          <CButton v-show="button" color="primary" shape="rounded-pill" @click="login">
            <CRow class="align-items-center">
              <div align="center">
                <strong>Login</strong>
              </div>
            </CRow>
          </CButton>
          <div v-show="loggedin" align="right">
            <CNavLink href="#/profile">Logged in as {{ profile.username }}</CNavLink>
          </div>
        </CNavItem>
      </CHeaderNav>
    </CContainer>
    <CHeaderDivider />
    <CContainer fluid>
      <AppBreadcrumb />
    </CContainer>
  </CHeader>
</template>

<script>
import AppBreadcrumb from './AppBreadcrumb'
import logo from '@/assets/images/logo.png'
export default {
  name: 'AppHeader',
  components: {
    AppBreadcrumb,
  },
  setup() {
    return {
      logo,
    }
  },
  data() {
    return {
      loggedin: false,
      button: true,
      admin: false,
      adminon: false,
      adminoff: true,
      profile: {},
      timer: "",
    }
  },
  created() {
    this.fetchData();
    this.timer = setInterval(this.fetchData, 60000);
  },
  methods: {
    async login() {
      var link = await fetch('/auth').then(response => response.json()).then(data => data);
      window.location.href = link;
    },
    async perms() {
      this.admin = !this.admin;
      this.adminon = !this.adminon;
      this.adminoff = !this.adminoff;
    },
    async fetchData() {
      if (this.$cookies.get("access_token")) {
        this.loggedin = true;
        this.button = false;
        this.profile = await fetch("/reddit/profile").then(response => response.json()).then(data => data);
      }
      else {
        this.loggedin = false;
        this.button = true;
      }
      // this.admin
    },
    cancelAutoUpdate() {
      clearInterval(this.timer);
    },
  },
  beforeUnmount() {
    this.cancelAutoUpdate();
  },
}
</script>
