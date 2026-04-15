<template>
    <q-layout view="hHh lpR fFf">
        <q-header elevated>
            <q-toolbar>
                <q-btn dense flat icon="menu" @click="toggleDrawer" />
                <q-toolbar-title class="text-weight-medium">
                    Data Science Applications Hub
                </q-toolbar-title>
                <q-btn
                    flat
                    dense
                    icon="upload_file"
                    label="Central Setup"
                    class="q-ml-sm"
                    to="/"
                />
                <q-btn
                    v-for="module in activeModules"
                    :key="module.id"
                    flat
                    dense
                    icon="table_view"
                    :label="module.label"
                    class="q-ml-sm"
                    :to="module.analysisRoute"
                />
            </q-toolbar>
        </q-header>

        <q-drawer
            v-model="drawerOpen"
            side="left"
            overlay
            bordered
            behavior="mobile"
        >
            <q-list>
                <q-item-label header class="text-weight-bold">
                    Active Modules
                </q-item-label>

                <q-item clickable to="/" exact @click="drawerOpen = false">
                    <q-item-section avatar>
                        <q-icon name="upload_file" />
                    </q-item-section>
                    <q-item-section>Central Setup</q-item-section>
                </q-item>

                <q-item
                    v-for="module in activeModules"
                    :key="module.id"
                    clickable
                    :to="module.analysisRoute"
                    exact
                    @click="drawerOpen = false"
                >
                    <q-item-section avatar>
                        <q-icon name="table_view" />
                    </q-item-section>
                    <q-item-section>{{ module.label }}</q-item-section>
                </q-item>
            </q-list>
        </q-drawer>

        <q-page-container>
            <router-view />
        </q-page-container>
    </q-layout>
</template>

<script setup lang="ts">
import { ref } from 'vue';

import { activeAnalysisModules } from '@/core/registry';

const drawerOpen = ref(false);
const activeModules = activeAnalysisModules;

function toggleDrawer() {
    drawerOpen.value = !drawerOpen.value;
}
</script>
